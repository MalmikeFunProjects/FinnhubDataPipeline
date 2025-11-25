import React from "react";
import { cn } from "@/utils"; // Utility for conditional classNames (if you have one)
import { InputProps } from "@/types";

const Input: React.FC<InputProps> = ({
  value,
  onChange,
  variant = "primary",
  text_variant = "primary",
  size = "md",
  fullWidth = false,
  disabled = false,
  placeholder,
  type = "text",
  className = "",
  ...rest
}) => {
  const baseClasses =
    `${className} rounded-md border focus:outline-none transition duration-200`;

  const sizeClasses = {
    sm: "py-1 px-2 text-sm",
    md: "py-2 px-3 text-base",
    lg: "py-3 px-4 text-lg",
  };

  const variantClasses = {
    primary: "border-gray-300 focus:ring-2 focus:ring-blue-500",
    secondary: "border-gray-400 focus:ring-2 focus:ring-gray-500",
    success: "border-green-400 focus:ring-2 focus:ring-green-500",
    danger: "border-red-400 focus:ring-2 focus:ring-red-500",
  };

  const textClasses  = {
    primary: "text-black",
    secondary: "text-gray-700",
    success: "text-green-500",
    error: "text-red-500"
  }
  // Width classes
  const widthClasses = fullWidth ? "w-full" : "";

  // Disabled classes
  const disabledClasses = disabled
    ? "opacity-50 cursor-not-allowed bg-gray-100"
    : "";
  return (
    <input
      type={type}
      className={cn(
        baseClasses,
        sizeClasses[size],
        variantClasses[variant],
        widthClasses,
        disabledClasses,
        textClasses[text_variant]
      )}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      {...rest}
    />
  );
};

export default Input;
