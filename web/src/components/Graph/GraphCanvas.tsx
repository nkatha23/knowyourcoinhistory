import { useCallback } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type NodeTypes,
  type NodeMouseHandler,
  type Node,
  type Edge,
  type OnNodesChange,
  applyNodeChanges,
  applyEdgeChanges,
  type OnEdgesChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import type { AppNodeData } from '../../types/graph';
import { useGraphStore } from '../../store/graph';
import TransactionNode from './TransactionNode';
import UTXONode from './UTXONode';
import EmptyState from './EmptyState';

const nodeTypes: NodeTypes = {
  txNode: TransactionNode,
  utxoNode: UTXONode,
};

export default function GraphCanvas() {
  const nodes = useGraphStore((s) => s.nodes) as unknown as Node[];
  const edges = useGraphStore((s) => s.edges) as Edge[];
  const setStoreNodes = useGraphStore((s) => s.setNodes);
  const setStoreEdges = useGraphStore((s) => s.setEdges);
  const selectNode = useGraphStore((s) => s.selectNode);
  const loadRootTx = useGraphStore((s) => s.loadRootTx);
  const recentSessions = useGraphStore((s) => s.recentSessions);
  const backendOnline = useGraphStore((s) => s.backendOnline);
  const theme = useGraphStore((s) => s.theme);

  const onNodesChange = useCallback<OnNodesChange>(
    (changes) =>
      setStoreNodes(applyNodeChanges(changes, nodes) as unknown as Node<AppNodeData>[]),
    [nodes, setStoreNodes],
  );

  const onEdgesChange = useCallback<OnEdgesChange>(
    (changes) => setStoreEdges(applyEdgeChanges(changes, edges)),
    [edges, setStoreEdges],
  );

  const onNodeClick = useCallback<NodeMouseHandler>(
    (_evt, node) => selectNode(node.id),
    [selectNode],
  );

  const onPaneClick = useCallback(() => selectNode(null), [selectNode]);

  const isEmpty = nodes.length === 0;

  return (
    <div className="relative w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.15}
        maxZoom={2.5}
        colorMode={theme}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color={theme === 'dark' ? '#374151' : '#d1d5db'}
        />
        <Controls showInteractive={false} />
        <MiniMap
          nodeStrokeWidth={2}
          nodeColor={(n) => {
            const d = n.data as unknown as AppNodeData;
            return d?.kind === 'tx' ? '#f7931a' : '#9ca3af';
          }}
          zoomable
          pannable
        />
      </ReactFlow>

      {isEmpty && (
        <EmptyState
          onLoadTxid={loadRootTx}
          recentSessions={recentSessions}
          backendOnline={backendOnline}
        />
      )}
    </div>
  );
}
