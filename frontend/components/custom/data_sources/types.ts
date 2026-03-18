export type TreeNode = {
  id: string;
  label: string;
  type: "group" | "database" | "table" | "file";
  children?: TreeNode[];
};
