#!/usr/bin/env python3
"""
Validate valuation accuracy on known recent sales.

Method:
1. Sample properties sold in last 6 months
2. Run valuation on each (excluding the property itself)
3. Calculate MAPE (Mean Absolute Percentage Error)
4. Analyze by county, property type, and price range

Target: MAPE < 25% for MVP (urban areas)

Usage:
    python3 scripts/validate_valuation_accuracy.py --sample-size 100
    python3 scripts/validate_valuation_accuracy.py --county Dublin --sample-size 50
"""

import asyncio
import asyncpg
import os
import sys
import argparse
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, 'backend')

from valuation.geocoder import ValuationGeocoder
from valuation.comparable_search import ComparableSearcher
from valuation.adjustments import MVPAdjuster
from valuation.calculator import ValuationCalculator
from valuation.validator import MVPValidator

load_dotenv('backend/.env')

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in backend/.env")
    sys.exit(1)


class ValuationAccuracyValidator:
    """Validate valuation accuracy against known sales."""

    def __init__(self, db_pool):
        self.db = db_pool
        self.geocoder = ValuationGeocoder(db_pool)
        self.searcher = ComparableSearcher(db_pool)
        self.adjuster = MVPAdjuster(db_pool)
        self.calculator = ValuationCalculator()
        self.validator = MVPValidator()

    async def sample_test_properties(
        self,
        sample_size: int = 100,
        county: Optional[str] = None,
        min_price: int = 100000,
        max_price: int = 1000000,
        months_back: int = 6
    ):
        """
        Sample properties for validation testing.

        Criteria:
        - Sold in last N months
        - Price between min and max (avoid extremes)
        - Has valid coordinates
        - Not marked as not_full_market_price

        Returns list of property dicts.
        """
        lookback_date = datetime.now() - timedelta(days=months_back * 30)

        filters = [
            "sale_date >= $1",
            "not_full_market_price = FALSE",
            "price BETWEEN $2 AND $3",
            "latitude IS NOT NULL",
            "longitude IS NOT NULL"
        ]
        params = [lookback_date, min_price, max_price]
        idx = 4

        if county:
            filters.append(f"LOWER(county) = LOWER(${idx})")
            params.append(county)
            idx += 1

        where = " AND ".join(filters)
        params.append(sample_size)

        query = f"""
            SELECT
                id, address, eircode, county,
                latitude, longitude,
                price, sale_date,
                bedrooms, property_type
            FROM properties
            WHERE {where}
            ORDER BY RANDOM()
            LIMIT ${idx}
        """

        rows = await self.db.fetch(query, *params)

        properties = []
        for row in rows:
            properties.append({
                'id': row['id'],
                'address': row['address'],
                'eircode': row['eircode'],
                'county': row['county'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'price': row['price'],
                'sale_date': row['sale_date'],
                'bedrooms': row['bedrooms'],
                'property_type': row['property_type']
            })

        return properties

    async def run_valuation(
        self,
        property_data: dict,
        exclude_property_id: int
    ) -> Optional[dict]:
        """
        Run valuation for a single property.

        Args:
            property_data: Property dict with lat/lon
            exclude_property_id: Property ID to exclude from comparables

        Returns:
            Valuation result dict or None if failed
        """
        try:
            # Step 1: Find comparables (exclude the property itself)
            comparables = await self.searcher.find_comparables(
                latitude=property_data['latitude'],
                longitude=property_data['longitude'],
                min_count=5,
                max_count=30,
                exclude_property_id=exclude_property_id
            )

            if len(comparables) < 5:
                return None

            # Step 2: Adjust prices for time difference
            target_date = property_data['sale_date']

            for comp in comparables:
                temporal_adj = await self.adjuster.adjust_temporal(
                    sale_price=comp['price'],
                    sale_date=comp['sale_date'],
                    target_date=target_date,
                    county=comp['county']
                )
                comp['adjusted_price'] = temporal_adj['adjusted_price']
                comp['adjustment_factor'] = temporal_adj['adjustment_factor']

            # Step 3: Calculate weights
            weights = self.adjuster.calculate_all_weights(comparables)

            for comp, weight in zip(comparables, weights):
                comp['weight'] = weight

            # Step 4: Calculate valuation
            valuation = self.calculator.calculate_valuation(comparables, weights)

            # Step 5: Validate
            validation = self.validator.validate(valuation, comparables)

            return {
                'estimate': valuation['estimate'],
                'confidence_interval': valuation['confidence_interval'],
                'confidence_level': validation.confidence_level.value,
                'quality_score': validation.quality_score,
                'n_comparables': len(comparables),
                'avg_distance_km': validation.avg_distance_km,
                'statistics': valuation['statistics']
            }

        except Exception as e:
            print(f"  ✗ Valuation failed: {e}")
            return None

    async def validate_sample(
        self,
        sample_size: int = 100,
        county: Optional[str] = None
    ):
        """
        Validate valuation accuracy on a sample of properties.

        Returns:
            DataFrame with validation results
        """
        print(f"\n{'='*70}")
        print(f"VALUATION ACCURACY VALIDATION")
        print(f"{'='*70}\n")

        # Sample test properties
        print(f"Sampling {sample_size} properties...")
        if county:
            print(f"County filter: {county}")

        properties = await self.sample_test_properties(
            sample_size=sample_size,
            county=county
        )

        print(f"✓ Sampled {len(properties)} properties\n")

        if len(properties) == 0:
            print("ERROR: No properties found matching criteria")
            return None

        print(f"Running valuations (excluding property itself as comparable)...\n")

        results = []
        success_count = 0
        failed_count = 0

        for i, prop in enumerate(properties, 1):
            print(f"[{i}/{len(properties)}] {prop['address'][:50]}", end=" ... ")

            try:
                valuation = await self.run_valuation(prop, prop['id'])

                if valuation is None:
                    print("✗ Insufficient comparables")
                    failed_count += 1
                    continue

                actual_price = prop['price']
                estimated_price = valuation['estimate']

                error_pct = abs(estimated_price - actual_price) / actual_price * 100

                results.append({
                    'property_id': prop['id'],
                    'address': prop['address'],
                    'county': prop['county'],
                    'property_type': prop['property_type'],
                    'bedrooms': prop['bedrooms'],
                    'actual_price': actual_price,
                    'estimated_price': estimated_price,
                    'error_pct': error_pct,
                    'confidence_level': valuation['confidence_level'],
                    'quality_score': valuation['quality_score'],
                    'n_comparables': valuation['n_comparables'],
                    'avg_distance_km': valuation['avg_distance_km'],
                    'ci_lower': valuation['confidence_interval']['lower'],
                    'ci_upper': valuation['confidence_interval']['upper'],
                    'ci_width_pct': valuation['confidence_interval']['width_pct']
                })

                print(f"✓ Error: {error_pct:.1f}% | Confidence: {valuation['confidence_level']}")
                success_count += 1

            except Exception as e:
                print(f"✗ Error: {e}")
                failed_count += 1

        print(f"\n{'='*70}")
        print(f"Completed: {success_count} successful, {failed_count} failed")
        print(f"{'='*70}\n")

        if success_count == 0:
            print("ERROR: No successful valuations")
            return None

        return pd.DataFrame(results)

    def analyze_results(self, df: pd.DataFrame):
        """Generate comprehensive accuracy analysis."""
        print(f"\n{'='*70}")
        print(f"ACCURACY ANALYSIS")
        print(f"{'='*70}\n")

        # Overall statistics
        print(f"Sample Size: {len(df)}")
        print(f"\nOverall MAPE: {df['error_pct'].mean():.1f}%")
        print(f"Median Error: {df['error_pct'].median():.1f}%")
        print(f"Std Dev: {df['error_pct'].std():.1f}%")
        print(f"Min Error: {df['error_pct'].min():.1f}%")
        print(f"Max Error: {df['error_pct'].max():.1f}%")

        # Error distribution
        print(f"\n--- Error Distribution ---")
        print(f"<10% error: {(df['error_pct'] < 10).sum()} ({(df['error_pct'] < 10).mean()*100:.1f}%)")
        print(f"<15% error: {(df['error_pct'] < 15).sum()} ({(df['error_pct'] < 15).mean()*100:.1f}%)")
        print(f"<20% error: {(df['error_pct'] < 20).sum()} ({(df['error_pct'] < 20).mean()*100:.1f}%)")
        print(f"<25% error: {(df['error_pct'] < 25).sum()} ({(df['error_pct'] < 25).mean()*100:.1f}%)")
        print(f"<30% error: {(df['error_pct'] < 30).sum()} ({(df['error_pct'] < 30).mean()*100:.1f}%)")
        print(f">50% error: {(df['error_pct'] > 50).sum()} ({(df['error_pct'] > 50).mean()*100:.1f}%)")

        # By county
        if df['county'].nunique() > 1:
            print(f"\n--- By County ---")
            county_stats = df.groupby('county')['error_pct'].agg([
                ('count', 'count'),
                ('mean', 'mean'),
                ('median', 'median'),
                ('std', 'std')
            ]).round(1)
            print(county_stats.to_string())

        # By confidence level
        print(f"\n--- By Confidence Level ---")
        conf_stats = df.groupby('confidence_level')['error_pct'].agg([
            ('count', 'count'),
            ('mean', 'mean'),
            ('median', 'median')
        ]).round(1)
        print(conf_stats.to_string())

        # By number of comparables
        print(f"\n--- By Number of Comparables ---")
        df['comp_bucket'] = pd.cut(
            df['n_comparables'],
            bins=[0, 5, 10, 20, 100],
            labels=['<5', '5-10', '10-20', '20+']
        )
        comp_stats = df.groupby('comp_bucket')['error_pct'].agg([
            ('count', 'count'),
            ('mean', 'mean'),
            ('median', 'median')
        ]).round(1)
        print(comp_stats.to_string())

        # By price range
        print(f"\n--- By Price Range ---")
        df['price_bucket'] = pd.cut(
            df['actual_price'],
            bins=[0, 200000, 300000, 400000, 500000, 1000000],
            labels=['<200k', '200-300k', '300-400k', '400-500k', '500k+']
        )
        price_stats = df.groupby('price_bucket')['error_pct'].agg([
            ('count', 'count'),
            ('mean', 'mean'),
            ('median', 'median')
        ]).round(1)
        print(price_stats.to_string())

        # By property type (if available)
        if df['property_type'].notna().sum() > 0:
            print(f"\n--- By Property Type ---")
            type_stats = df[df['property_type'].notna()].groupby('property_type')['error_pct'].agg([
                ('count', 'count'),
                ('mean', 'mean'),
                ('median', 'median')
            ]).round(1)
            print(type_stats.to_string())

        # Confidence interval coverage
        print(f"\n--- Confidence Interval Coverage ---")
        df['in_ci'] = (df['actual_price'] >= df['ci_lower']) & (df['actual_price'] <= df['ci_upper'])
        coverage = df['in_ci'].mean() * 100
        print(f"Actual price within CI: {df['in_ci'].sum()} / {len(df)} ({coverage:.1f}%)")
        print(f"Average CI width: {df['ci_width_pct'].mean():.1f}%")

        # Quality score vs error correlation
        print(f"\n--- Quality Score Analysis ---")
        print(f"Average quality score: {df['quality_score'].mean():.2f}")
        print(f"Quality score correlation with error: {df[['quality_score', 'error_pct']].corr().iloc[0, 1]:.3f}")

        # Top 10 worst predictions
        print(f"\n--- Top 10 Largest Errors ---")
        worst = df.nlargest(10, 'error_pct')[['address', 'actual_price', 'estimated_price', 'error_pct', 'confidence_level', 'county']]
        for idx, row in worst.iterrows():
            print(f"{row['error_pct']:>5.1f}% | €{row['actual_price']:>7,} → €{row['estimated_price']:>7,} | "
                  f"{row['confidence_level']:>6} | {row['county']:<15} | {row['address'][:40]}")

        # Target achievement
        print(f"\n{'='*70}")
        print(f"TARGET ACHIEVEMENT")
        print(f"{'='*70}")
        urban_mape = df['error_pct'].mean()
        target_urban = 25.0
        target_rural = 35.0

        if urban_mape <= target_urban:
            print(f"✓ PASS: Urban MAPE {urban_mape:.1f}% ≤ {target_urban}% target")
        else:
            print(f"✗ MISS: Urban MAPE {urban_mape:.1f}% > {target_urban}% target (delta: +{urban_mape - target_urban:.1f}%)")

        print(f"\nRecommendations:")
        if urban_mape > target_urban:
            print("- Consider Phase 2 enhancements (feature-based adjustments)")
            print("- Continue property enrichment (bedrooms, property type)")
            print("- Review worst predictions for patterns")
        else:
            print("- MVP accuracy target achieved!")
            print("- Ready for Beta launch")
            print("- Continue monitoring with real user requests")


async def main():
    parser = argparse.ArgumentParser(description='Validate valuation accuracy')
    parser.add_argument('--sample-size', type=int, default=100,
                        help='Number of properties to test (default: 100)')
    parser.add_argument('--county', type=str, default=None,
                        help='Filter to specific county')
    parser.add_argument('--output', type=str, default='valuation_accuracy_results.csv',
                        help='Output CSV file (default: valuation_accuracy_results.csv)')
    parser.add_argument('--json', action='store_true',
                        help='Also output results as JSON')

    args = parser.parse_args()

    # Connect to database
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=3,
        statement_cache_size=0,
        command_timeout=30
    )

    try:
        validator = ValuationAccuracyValidator(pool)

        # Run validation
        df = await validator.validate_sample(
            sample_size=args.sample_size,
            county=args.county
        )

        if df is not None and len(df) > 0:
            # Analyze results
            validator.analyze_results(df)

            # Save results
            df.to_csv(args.output, index=False)
            print(f"\n✓ Results saved to {args.output}")

            if args.json:
                json_output = args.output.replace('.csv', '.json')
                df.to_json(json_output, orient='records', indent=2)
                print(f"✓ Results saved to {json_output}")

            # Summary stats for quick reference
            print(f"\n{'='*70}")
            print(f"QUICK SUMMARY")
            print(f"{'='*70}")
            print(f"MAPE: {df['error_pct'].mean():.1f}%")
            print(f"Median Error: {df['error_pct'].median():.1f}%")
            print(f"Within 20%: {(df['error_pct'] < 20).mean()*100:.1f}%")
            print(f"CI Coverage: {((df['actual_price'] >= df['ci_lower']) & (df['actual_price'] <= df['ci_upper'])).mean()*100:.1f}%")
            print(f"{'='*70}\n")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
