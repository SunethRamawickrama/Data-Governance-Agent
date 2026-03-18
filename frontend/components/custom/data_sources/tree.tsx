"use client";

import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronRight } from "lucide-react";
import { TreeNode as TreeNodeType } from "./types";

export function TreeNode({ node }: { node: TreeNodeType }) {
  const [expanded, setExpanded] = useState(false);

  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="ml-2">
      <div className="flex items-center gap-2 py-1">
        {hasChildren && (
          <ChevronRight
            className={`h-4 w-4 cursor-pointer transition-transform ${
              expanded ? "rotate-90" : ""
            }`}
            onClick={() => setExpanded(!expanded)}
          />
        )}

        <Checkbox />

        <span className="text-sm">{node.label}</span>
      </div>

      {expanded && hasChildren && (
        <div className="ml-4 border-l pl-2">
          {node.children!.map((child) => (
            <TreeNode key={child.id} node={child} />
          ))}
        </div>
      )}
    </div>
  );
}
