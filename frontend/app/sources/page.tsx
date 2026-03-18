import { DataSourcesPanel } from "@/components/custom/data_sources/dataSourcesPanel";
import { dataSources } from "@/lib/mock-data";

export default function SourcesPage() {
  return (
    <div className="p-6">
      <DataSourcesPanel data={dataSources} />
    </div>
  );
}
