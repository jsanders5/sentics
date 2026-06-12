interface SkeletonProps {
  className?: string;
  count?: number;
}

export function Skeleton({ className = "h-12 w-full", count = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse rounded bg-[--bg-raised] ${className}`}
        />
      ))}
    </>
  );
}
