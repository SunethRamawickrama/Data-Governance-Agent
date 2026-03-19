import { DataSourcesPanel } from "@/components/custom/data_sources/dataSourcesPanel";
import { dataSources } from "@/lib/mock-data";
import AddSourceForm from "@/components/custom/data_sources/AddSourceForm";

export default function SourcesPage() {
  return (
    <div className="w-1/2 flex gap-6">
      <div className="p-6">
        <DataSourcesPanel data={dataSources} />
      </div>

      <div className="w-1/2">
        <AddSourceForm />
      </div>
    </div>
  );
}
