import { useState } from "react";
import { estimatePropertyValue } from "../api";
import type { ValuationResponse, ComparableProperty } from "../types";

export function ValuationPage() {
  const [address, setAddress] = useState("");
  const [eircode, setEircode] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!address.trim()) {
      setError("Please enter an address");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await estimatePropertyValue({
        address: address.trim(),
        eircode: eircode.trim() || undefined,
      });

      setResult(response);
    } catch (err: any) {
      setError(err.message || "Valuation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => `€${price.toLocaleString("en-IE")}`;

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case "high":
        return "text-green-600 bg-green-50 border-green-200";
      case "medium":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "low":
        return "text-orange-600 bg-orange-50 border-orange-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getWarningColor = (level: string) => {
    switch (level) {
      case "error":
        return "bg-red-50 border-red-200 text-red-800";
      case "warning":
        return "bg-yellow-50 border-yellow-200 text-yellow-800";
      case "info":
        return "bg-blue-50 border-blue-200 text-blue-800";
      default:
        return "bg-gray-50 border-gray-200 text-gray-800";
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-3">Property Valuation</h1>
        <p className="text-gray-600 text-lg">
          Get an instant automated estimate based on comparable sales in your area
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
              Property Address *
            </label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g., 28 Slane Road, Crumlin, Dublin 12"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="eircode" className="block text-sm font-medium text-gray-700 mb-1">
              Eircode (Optional)
            </label>
            <input
              id="eircode"
              type="text"
              value={eircode}
              onChange={(e) => setEircode(e.target.value.toUpperCase())}
              placeholder="e.g., D12 XY34"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength={8}
              disabled={loading}
            />
            <p className="text-sm text-gray-500 mt-1">
              Adding an Eircode improves geocoding accuracy
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="w-full bg-blue-600 text-white font-medium px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Calculating..." : "Get Valuation"}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Valuation Summary */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Estimated Value</h2>

            <div className="mb-4">
              <div className="text-5xl font-bold text-blue-600 mb-2">
                {formatPrice(result.estimate)}
              </div>
              <div className="text-sm text-gray-600">
                Confidence Range: {formatPrice(result.confidence_interval.lower)} -{" "}
                {formatPrice(result.confidence_interval.upper)}
                <span className="ml-2 text-xs">
                  (±{result.confidence_interval.width_pct.toFixed(1)}%)
                </span>
              </div>
            </div>

            <div
              className={`inline-block px-4 py-2 rounded-lg border font-medium ${getConfidenceColor(
                result.validation.confidence_level
              )}`}
            >
              {result.validation.confidence_level.toUpperCase()} CONFIDENCE
              <span className="ml-2 text-sm opacity-75">
                (Quality: {(result.validation.quality_score * 100).toFixed(0)}/100)
              </span>
            </div>

            <div className="mt-4 text-sm text-gray-600 space-y-1">
              <p>• Based on {result.validation.n_comparables} comparable sales</p>
              <p>
                • Average distance: {result.validation.avg_distance_km.toFixed(1)} km
              </p>
              <p>
                • Processed in {result.metadata.processing_time_ms}ms by{" "}
                {result.metadata.algorithm_version}
              </p>
            </div>

            {/* Warnings */}
            {result.validation.warnings.length > 0 && (
              <div className="mt-4 space-y-2">
                {result.validation.warnings.map((warning, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-sm ${getWarningColor(
                      warning.level
                    )}`}
                  >
                    <span className="font-medium">
                      {warning.level.charAt(0).toUpperCase() + warning.level.slice(1)}:
                    </span>{" "}
                    {warning.message}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Statistics */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-xl font-bold mb-4">Statistical Analysis</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-600">Median Price</div>
                <div className="text-lg font-semibold">
                  {formatPrice(result.statistics.median_price)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Mean Price</div>
                <div className="text-lg font-semibold">
                  {formatPrice(result.statistics.mean_price)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Price Range</div>
                <div className="text-lg font-semibold">
                  {formatPrice(result.statistics.min_price)} -{" "}
                  {formatPrice(result.statistics.max_price)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Std Deviation</div>
                <div className="text-lg font-semibold">
                  €{result.statistics.std_dev.toLocaleString("en-IE", { maximumFractionDigits: 0 })}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Coefficient of Variation</div>
                <div className="text-lg font-semibold">
                  {(result.statistics.coefficient_of_variation * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          {/* Comparables Table */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-xl font-bold mb-4">
              Comparable Sales ({result.comparables.length})
            </h3>

            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Address
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sale Price
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Adjusted Price
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Distance
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Weight
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.comparables.map((comp) => (
                    <tr key={comp.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{comp.address}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-right">
                        {formatPrice(comp.price)}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
                        {formatPrice(comp.adjusted_price)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 text-right">
                        {(comp.distance_m / 1000).toFixed(2)} km
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 text-right">
                        {(comp.weight * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="bg-gray-50 rounded-lg p-6 text-sm text-gray-700">
            <p className="font-semibold mb-2">Important Disclaimer</p>
            <p>
              This valuation is an automated estimate based on comparable sales data from
              Ireland's Property Price Register. It should be used as a starting point for
              understanding market value, not as a definitive assessment. For official
              valuations (mortgage applications, legal matters, estate planning), you should
              always consult a qualified property valuer.
            </p>
          </div>
        </>
      )}

      {/* Help Text (when no results) */}
      {!result && !loading && !error && (
        <div className="bg-blue-50 rounded-lg p-6 text-sm text-blue-900">
          <p className="font-semibold mb-2">How it works</p>
          <ul className="list-disc list-inside space-y-1">
            <li>We find similar properties sold recently in your area</li>
            <li>Prices are adjusted for time using county-level market trends</li>
            <li>A weighted average is calculated based on distance and recency</li>
            <li>Results include a confidence level and comparable sales details</li>
          </ul>
        </div>
      )}
    </div>
  );
}
