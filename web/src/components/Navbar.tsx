"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/search", label: "Search" },
    { href: "/upload", label: "Upload" },
    { href: "/health", label: "Health" },
  ];

  return (
    <nav className="sticky top-0 z-50 text-black shadow-md">
      <div className="max-w-7xl mx-auto flex items-center px-6 py-3 space-x-4 ">
        <div className="text-lg font-bold tracking-wide">CargoRisk Rader</div>

        <div className="flex space-x-4 text-sm font-medium">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`hover:text-gray-500 transition-colors ${pathname === link.href ? "font-bold" : ""}`}>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
