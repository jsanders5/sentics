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
        console.log("[useCategories] Fetching categories...");
        const response = await fetch("/api/categories");
        console.log("[useCategories] Response status:", response.status);
        if (!response.ok) {
          const text = await response.text();
          console.error("[useCategories] Error response:", text);
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        console.log("[useCategories] Data loaded:", data.categories?.length || 0, "categories");
        setCategories(data.categories || []);
        setError(null);
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Failed to load categories";
        console.error("[useCategories] Error:", errMsg);
        setError(errMsg);
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
