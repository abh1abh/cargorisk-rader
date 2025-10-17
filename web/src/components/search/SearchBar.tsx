type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  placeholder?: string;
};
export default function SearchBar({ value, onChange, onSubmit, placeholder }: Props) {
  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => (e.key === "Enter" ? onSubmit() : null)}
        placeholder={placeholder}
        className="border p-2 rounded w-full"
      />
      <button onClick={onSubmit} className="px-3 py-2 border rounded">
        Search
      </button>
    </div>
  );
}
