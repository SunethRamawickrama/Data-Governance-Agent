// lib/mock-data.ts

import { TreeNode } from "@/components/custom/data_sources/types";

export const dataSources: TreeNode[] = [
  {
    id: "databases",
    label: "Databases",
    type: "group",
    children: [
      {
        id: "ads-db",
        label: "ads-db",
        type: "database",
        children: [
          { id: "campaigns", label: "campaigns", type: "table" },
          { id: "ad_clicks", label: "ad_clicks", type: "table" },
        ],
      },
      {
        id: "governance-db",
        label: "governance-db",
        type: "database",
        children: [{ id: "users", label: "users", type: "table" }],
      },
    ],
  },
];
