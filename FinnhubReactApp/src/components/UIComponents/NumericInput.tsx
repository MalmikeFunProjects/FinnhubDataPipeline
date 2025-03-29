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
}) => {
  const { initialValue, minValue, maxValue, defaultValue } = config;
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
    [minValue, maxValue]
  );

  const safeSetValue = useCallback(
    (newValue: number | undefined) => {
      const constrainedValue = constrainValue(newValue);
      setValue(constrainedValue);
      return constrainedValue;
    },
    [constrainValue]
  );

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const stringValue = event.target.value;
    const numericValue = parseFloat(stringValue);
    if (!isNaN(numericValue)) {
      safeSetValue(numericValue);
    } else if (stringValue === "") {
      safeSetValue(defaultValue || undefined);
    }
  };

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
  const [currentEvent, setCurrentEvent] = useState<React.ChangeEvent<HTMLInputElement> | undefined>(undefined)
  const { value, handleChange } = useNumericInput({
    initialValue: typeof propValue === "number" ? propValue? propValue: defaultValue : undefined,
    minValue: min,
    maxValue: max,
    defaultValue: defaultValue,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentEvent(e);
    handleChange(e);
  };

  useEffect(() => {
    if(currentEvent){
      propOnChange?.({
        ...currentEvent,
        target: {
          ...currentEvent.target,
          value: String(value),
        },
      } as React.ChangeEvent<HTMLInputElement>);
    }
  }, [value]);

  return (
    <Input
      type="number"
      value={propValue ?? ""}
      onChange={handleInputChange}
      min={min}
      max={max}
      {...props}
    />
  );
};

export default NumericInput;
