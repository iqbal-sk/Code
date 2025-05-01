// src/features/problems/ProblemDetailPage.tsx
import React, {JSX} from 'react';
import { useParams } from 'react-router-dom';

export default function ProblemDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Problem Detail: {id}</h1>
      {/* TODO: Render problem details and CodeEditor component */}
    </div>
  );
}