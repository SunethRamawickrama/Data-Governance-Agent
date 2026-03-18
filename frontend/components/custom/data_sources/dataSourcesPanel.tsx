"use client";

import { TreeNode } from "./tree";
import { TreeNode as TreeNodeType } from "./types";

export function DataSourcesPanel({ data }: { data: TreeNodeType[] }) {
  return (
    <div className="rounded-2xl border p-4 shadow-sm">
      <h2 className="text-lg font-semibold mb-3">Data Sources</h2>

      {data.map((node) => (
        <TreeNode key={node.id} node={node} />
      ))}
    </div>
  );
}
