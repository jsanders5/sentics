"use client";

import { useState, useEffect } from "react";
import { Category } from "@/app/types";

interface UseCategoriesResult {
  categories: Category[];
  loading: boolean;
  error: string | null;
}

export function useCategories(): UseCategoriesResult {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/categories");
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        setCategories(data.categories || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load categories");
        setCategories([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
    const interval = setInterval(fetchCategories, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return { categories, loading, error };
}
