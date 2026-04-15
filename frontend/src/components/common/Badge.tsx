import clsx from "clsx";

interface Props {
  label: string;
  color?: string;
}

export default function Badge({ label, color = "bg-gray-100 text-gray-700" }: Props) {
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", color)}>
      {label}
    </span>
  );
}
