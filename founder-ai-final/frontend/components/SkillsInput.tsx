"use client";

import { useState, KeyboardEvent } from "react";
import { X } from "lucide-react";

interface SkillsInputProps {
  value: string[];
  onChange: (skills: string[]) => void;
  placeholder?: string;
}

export default function SkillsInput({ value, onChange, placeholder = "Type a skill and press Enter" }: SkillsInputProps) {
  const [input, setInput] = useState("");

  const add = () => {
    const trimmed = input.trim().toLowerCase();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
    }
    setInput("");
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add();
    }
    if (e.key === "Backspace" && !input && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  return (
    <div className="flex flex-wrap gap-2 p-2 border border-gray-300 rounded-lg min-h-[44px] focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 bg-white">
      {value.map((s) => (
        <span key={s} className="flex items-center gap-1 bg-indigo-100 text-indigo-700 text-xs font-medium px-2.5 py-1 rounded-full">
          {s}
          <button type="button" onClick={() => onChange(value.filter((x) => x !== s))}>
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        className="flex-1 min-w-[120px] text-sm outline-none bg-transparent placeholder:text-gray-400"
        placeholder={value.length === 0 ? placeholder : "Add more…"}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        onBlur={add}
      />
    </div>
  );
}
