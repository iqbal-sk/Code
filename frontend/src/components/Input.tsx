import React, { InputHTMLAttributes, JSX } from 'react';

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export default function Input(props: InputProps): JSX.Element {
  return <input {...props} />;
}
