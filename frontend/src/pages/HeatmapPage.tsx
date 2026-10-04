import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import Breadcrumbs from "../components/Breadcrumbs";
import HeatmapBody from "../components/HeatmapBody";
import { usePageMeta } from "../hooks/usePageMeta";

export default function HeatmapPage() {
  const crumbs = [{ name: "House Price Growth Map", url: "/heatmap" }];
  const meta = usePageMeta(
    "Ireland House Price Growth Map",
    "An interactive map showing where house prices are rising fastest across Ireland. Each area is coloured by the change in median sale price between two periods of the Property Price Register — revealing the hottest and coolest local markets.",
    crumbs,
  );

  return (
    <>
      {meta}
      <PageHeader title="Ireland House Price Growth Map" titleAsHeading={false} />
      <div className="content-page">
        <Breadcrumbs items={crumbs} />
        <h1>Ireland House Price Growth Map</h1>
        <HeatmapBody />
      </div>
      <Footer />
    </>
  );
}
