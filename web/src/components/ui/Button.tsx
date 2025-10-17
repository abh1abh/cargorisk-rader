import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
}

const variantStyles: Record<string, string> = {
  primary: `bg-gradient-to-r from-gray-800 to-black
            hover:from-gray-700 hover:to-gray-900
            text-white shadow-md shadow-gray-400/20`,
  secondary: `bg-gradient-to-r from-gray-200 to-gray-300
              hover:from-gray-300 hover:to-gray-400
              text-gray-800 shadow-md shadow-gray-500/20`,
  danger: `bg-gradient-to-r from-red-600 to-red-700
           hover:from-red-500 hover:to-red-600
           text-white shadow-md shadow-red-400/20`,
};

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  disabled,
  className = "",
  ...props
}) => {
  return (
    <button
      disabled={disabled}
      className={`px-8 py-3 mr-5 rounded-full text-sm font-semibold
         hover:scale-105 transition-all duration-300
         disabled:opacity-60 disabled:cursor-not-allowed
         cursor-pointer
         ${variantStyles[variant] || variantStyles.primary}
         ${className}`}
      {...props}>
      {children}
    </button>
  );
};
