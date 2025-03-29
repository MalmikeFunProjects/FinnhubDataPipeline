// Common prop types
export interface ButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "success" | "danger";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  onClick?: (event?: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
}

// Override the value type based on the 'type' prop
export type InputValueProp<T extends InputProps["type"]> = T extends "number"
  ? number | undefined
  : string | number | undefined;

export interface InputProps {
  children?: React.ReactNode;
  value?: InputValueProp<InputProps["type"]>; // Dynamically set value type
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  placeholder?: string;
  variant?: "primary" | "secondary" | "success" | "danger";
  text_variant?: "primary" | "secondary" | "success" | "error";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  disabled?: boolean;
  type?:
    | "text"
    | "password"
    | "number"
    | "email"
    | "date"
    | "time"
    | "datetime-local";
  className?: string;
  error?: string;
  helperText?: string;
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
}
