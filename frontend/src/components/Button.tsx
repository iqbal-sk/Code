import React, { ReactNode, JSX } from 'react';

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}

export default function Button({ children, onClick, className }: ButtonProps): JSX.Element {
  return (
    <button onClick={onClick} className={className}>
      {children}
    </button>
  );
}
