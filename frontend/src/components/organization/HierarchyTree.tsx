'use client';

import { HierarchyNode } from '@/types';

interface HierarchyTreeProps {
  nodes: HierarchyNode[];
  title: string;
}

interface TreeNodeProps {
  node: HierarchyNode;
  level: number;
}

function TreeNode({ node, level }: TreeNodeProps) {
  const indent = level * 24;

  return (
    <div>
      <div
        className="flex items-center py-2 px-4 hover:bg-gray-50 rounded"
        style={{ paddingLeft: `${indent + 16}px` }}
      >
        <div className="flex-1">
          <div className="flex items-center">
            {level > 0 && (
              <span className="text-gray-400 mr-2">
                └─
              </span>
            )}
            <span className="font-medium text-gray-900">{node.name}</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            {node.employee_count} {node.employee_count === 1 ? 'employee' : 'employees'}
          </span>
        </div>
      </div>
      {node.children && node.children.length > 0 && (
        <div>
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function HierarchyTree({ nodes, title }: HierarchyTreeProps) {
  if (!nodes || nodes.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No {title.toLowerCase()} hierarchy available.
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="space-y-1">
        {nodes.map((node) => (
          <TreeNode key={node.id} node={node} level={0} />
        ))}
      </div>
    </div>
  );
}
