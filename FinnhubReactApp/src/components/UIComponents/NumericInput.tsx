import React, {
  useState,
  useCallback,
  useEffect,
} from "react";
import { InputProps } from "@/types";
import Input from "@/components/UIComponents/Input";

// Numeric Input Hook
const useNumericInput = (config: {
  initialValue?: number;
  minValue?: number;
  maxValue?: number;
  defaultValue?: number;
  onChange?: (value: number | undefined) => void;
}) => {
  const { initialValue, minValue, maxValue, defaultValue, onChange } = config;
  const [value, setValue] = useState<number | undefined>(initialValue);

  const constrainValue = useCallback(
    (inputValue: number | undefined) => {

      if (inputValue === undefined) return defaultValue || undefined;
      let constrainedValue = inputValue;

      if (minValue !== undefined) {
        constrainedValue = Math.max(constrainedValue, minValue);
      }

      if (maxValue !== undefined) {
        constrainedValue = Math.min(constrainedValue, maxValue);
      }

      return constrainedValue;
    },
    [minValue, maxValue, defaultValue]
  );

  const safeSetValue = useCallback(
    (newValue: number | undefined) => {
      const constrainedValue = constrainValue(newValue);
      setValue(constrainedValue);
      onChange?.(constrainedValue);
      return constrainedValue;
    },
    [constrainValue, onChange]
  );

  // Update local state when initialValue changes from props
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const stringValue = event.target.value;

    if (stringValue.trim() === "") {
      safeSetValue(undefined);
    } else {
      const numericValue = parseFloat(stringValue);
      if (!isNaN(numericValue)) {
        safeSetValue(numericValue);
      }else{
        safeSetValue(undefined);
      }
    }
  }, [safeSetValue]);

  return {
    value,
    setValue: safeSetValue,
    handleChange,
  };
};

// Numeric Input Component with Enhanced Functionality
const NumericInput: React.FC<InputProps> = ({
  min,
  max,
  defaultValue,
  value: propValue,
  onChange: propOnChange,
  ...props
}) => {
  const numericPropValue = () => propValue !== undefined && propValue !== ""
    ? typeof propValue === "number"
      ? propValue
      : Number(propValue)
    : undefined;


  const { value, handleChange } = useNumericInput({
    initialValue: numericPropValue(),
    minValue: min,
    maxValue: max,
    defaultValue: defaultValue !== undefined ? Number(defaultValue) : undefined,
    onChange: (newValue) => {
      if (propOnChange) {
        // Create a synthetic event to match the expected interface
        const syntheticEvent = {
          target: {
            value: newValue !== undefined ? String(newValue) : "",
          },
          // Add other event properties as needed
          preventDefault: () => {},
          stopPropagation: () => {},
        } as React.ChangeEvent<HTMLInputElement>;
        propOnChange(syntheticEvent);
      }
    }
  });

  // The displayed value should come from the internal state
  const displayValue = value !== undefined ? String(value) : "";

  return (
    <Input
      type="number"
      value={displayValue}
      onChange={handleChange}
      min={min}
      max={max}
      {...props}
    />
  );
};

export default NumericInput;
