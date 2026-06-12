"use client";

import { Category } from "@/app/types";
import { CategoryMomentumCard } from "./CategoryMomentumCard";
import { Skeleton } from "@/app/components/shared/Skeleton";

interface CategoryPanelProps {
  categories: Category[];
  loading: boolean;
  selectedCategory?: string;
  onSelectCategory: (category: string) => void;
}

export function CategoryPanel({
  categories,
  loading,
  selectedCategory,
  onSelectCategory,
}: CategoryPanelProps) {
  const passingCategories = categories.filter((c) => c.momentum_score >= 40);
  const sortedCategories = [...passingCategories].sort(
    (a, b) => b.momentum_score - a.momentum_score
  );

  return (
    <aside
      className="hidden md:flex w-56 flex-col p-4 overflow-y-auto"
      style={{
        backgroundColor: 'var(--bg-base)',
        borderRight: '1px solid var(--border)'
      }}
    >
      <div className="mb-4">
        <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[--text-secondary] mb-3">
          Category Momentum
        </h2>
        {loading ? (
          <Skeleton className="h-24 w-full" count={3} />
        ) : sortedCategories.length === 0 ? (
          <p className="text-sm text-[--text-muted]">No passing categories</p>
        ) : (
          <div className="space-y-2">
            {/* "All Categories" button */}
            <button
              onClick={() => onSelectCategory("All")}
              className={`w-full text-left rounded-lg border p-3 transition-all text-sm font-medium ${
                selectedCategory === "All"
                  ? "border-[--accent] bg-[--bg-raised] ring-2 ring-[--accent] text-[--accent]"
                  : "border-[--border] bg-[--bg-surface] text-[--text-secondary] hover:bg-[--bg-raised]"
              }`}
            >
              All Categories
            </button>

            {/* Category cards */}
            {sortedCategories.map((category) => (
              <CategoryMomentumCard
                key={category.name}
                category={category}
                isSelected={selectedCategory === category.name}
                onClick={() => onSelectCategory(category.name)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
