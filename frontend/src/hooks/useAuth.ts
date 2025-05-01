import { useState, useEffect } from 'react';

export default function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  // …
  return { isAuthenticated };
}
