import React from 'react';
import { ButtonProps } from '@/types';

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  type = 'button',
  onClick,
}) => {
  // Base classes
  const baseClasses = "font-bold rounded focus:outline-none focus:ring-2";

  // Size classes
  const sizeClasses = {
    sm: "py-1 px-2 text-sm",
    md: "py-2 px-4 text-base",
    lg: "py-3 px-6 text-lg",
  };

  // Variant classes
  const variantClasses = {
    primary: "bg-blue-500 hover:bg-blue-600 text-white focus:ring-blue-300",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-800 focus:ring-gray-300",
    success: "bg-green-500 hover:bg-green-600 text-white focus:ring-green-300",
    danger: "bg-red-500 hover:bg-red-600 text-white focus:ring-red-300",
  };

  // Width classes
  const widthClasses = fullWidth ? "w-full" : "";

  // Disabled classes
  const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";

  return (
    <button
      type={type}
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${widthClasses} ${disabledClasses}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;
