import { Loader2 } from "lucide-react";

export default function Spinner({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className={`animate-spin text-primary-600 ${className}`} />
    </div>
  );
}
