"use client";

import React, { useState, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  type Node,
  type Edge,
  type NodeChange,
  type EdgeChange,
  type Connection,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Webhook Trigger (POST /lead_created)' },
    position: { x: 250, y: 25 },
    className: 'bg-primary-container text-on-primary-container border-primary font-medium text-sm p-3 rounded-lg shadow-sm',
  },
  {
    id: '2',
    data: { label: 'Analyze Lead with AI' },
    position: { x: 250, y: 125 },
    className: 'bg-surface text-on-surface border-outline-variant text-sm p-3 rounded-lg shadow-sm',
  },
  {
    id: '3',
    type: 'output',
    data: { label: 'Send Slack Notification' },
    position: { x: 250, y: 250 },
    className: 'bg-secondary-container text-on-secondary-container border-secondary font-medium text-sm p-3 rounded-lg shadow-sm',
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
];

export default function WorkflowBuilderPage() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  const onNodesChange = useCallback(
    (changes: NodeChange<Node>[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge>[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    []
  );

  const addNode = (type: string, label: string) => {
    const newNode: Node = {
      id: Math.random().toString(),
      type,
      data: { label },
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      className: 'bg-surface text-on-surface border-outline-variant text-sm shadow-sm p-3 rounded-lg',
    };
    setNodes((nds) => [...nds, newNode]);
  };

  return (
    <main className="ml-(--spacing-sidebar-width) h-screen flex flex-col pt-16">
      <div className="px-6 py-4 border-b border-outline-variant bg-surface flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-on-surface">Visual Workflow Builder</h1>
          <p className="text-sm text-on-surface-variant">Design, connect, and deploy custom AI automations.</p>
        </div>
        <button 
          onClick={() => window.location.href = "/workflows"}
          className="text-sm text-on-surface-variant hover:text-on-surface flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
          Exit Builder
        </button>
      </div>

      <div className="flex-1 w-full h-full relative bg-surface-container-lowest">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          className="w-full h-full"
        >
          <Background color="#ccc" gap={16} />
          <Controls className="bg-surface border-outline-variant" />
          <Panel position="top-left" className="bg-surface p-4 rounded-xl shadow-md border border-outline-variant flex flex-col gap-2 w-64 m-4">
            <h3 className="font-semibold text-on-surface mb-2 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">build_circle</span>
              Node Toolbox
            </h3>
            
            <button 
              onClick={() => addNode('input', 'New Trigger')}
              className="bg-primary-container text-on-primary-container px-3 py-2 rounded-lg text-sm text-left hover:opacity-90 transition-opacity flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">bolt</span>
              Add Trigger
            </button>
            
            <button 
              onClick={() => addNode('default', 'AI Action')}
              className="bg-surface-container text-on-surface px-3 py-2 rounded-lg border border-outline-variant text-sm text-left hover:bg-surface-variant transition-colors flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">psychology</span>
              Add AI Action
            </button>
            
            <button 
              onClick={() => addNode('output', 'Integration')}
              className="bg-secondary-container text-on-secondary-container px-3 py-2 rounded-lg text-sm text-left hover:opacity-90 transition-opacity flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">api</span>
              Add Integration
            </button>
            
            <div className="mt-4 pt-4 border-t border-outline-variant">
              <button 
                onClick={() => alert("Workflow deployed successfully to the backend!")}
                className="w-full bg-primary text-on-primary px-3 py-2.5 rounded-lg text-sm font-bold hover:opacity-90 active:scale-95 transition-all cursor-pointer flex items-center justify-center gap-2 shadow-sm"
              >
                <span className="material-symbols-outlined text-[18px]">cloud_upload</span>
                Deploy Workflow
              </button>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </main>
  );
}
