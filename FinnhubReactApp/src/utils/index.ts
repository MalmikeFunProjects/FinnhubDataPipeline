import { DateTime, Duration } from 'luxon';

// Enums for type safety
enum TimeDeltaType {
  Years = 'years',
  Months = 'months',
  Weeks = 'weeks',
  Days = 'days',
  Hours = 'hours',
  Minutes = 'minutes',
  Seconds = 'seconds',
  Milliseconds = 'milliseconds',
}

enum TimeReturnType {
  MS = 'MS',
  STR_FORMAT = 'STR_FORMAT',
  DATETIME = 'DATETIME',
  DATE = 'DATE',
}

export interface AdjustDatetimeOptions {
  duration?: Partial<Record<TimeDeltaType, number>>;
  returnType?: TimeReturnType;
  originalDate?: DateTime | Date | null;
  startOfDay?: boolean;
  previousDate?: boolean;
  dateFormat?: string;
}

/**
 * Utility function to conditionally join CSS class names
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

/**
 * Converts a DateTime object or formatted string to milliseconds
 */
export function datetimeToMs(datetimeVal: DateTime | string): number {
  if (typeof datetimeVal === 'string') {
    return DateTime.fromFormat(datetimeVal, 'yyyy-MM-dd HH:mm:ss').toMillis();
  }
  return datetimeVal.toMillis();
}

/**
 * Converts milliseconds to a formatted datetime string
 */
export function msToDatetime(timestampMs: number, timezone?: string): string {
  const dt = timezone
    ? DateTime.fromMillis(timestampMs).setZone(timezone)
    : DateTime.fromMillis(timestampMs);

  return dt.toFormat('yyyy-MM-dd HH:mm:ss');
}

/**
 * Adjusts a datetime by a specified duration and returns it in the requested format
 */
export function adjustDatetime(options: AdjustDatetimeOptions = {}): number | string | DateTime | Date {
  const {
    duration = null,
    returnType = TimeReturnType.MS,
    originalDate = null,
    startOfDay = false,
    previousDate = true,
    dateFormat = 'yyyy-MM-dd HH:mm:ss'
  } = options;
  // Initialize the DateTime object
  let adjustedDateTime: DateTime = originalDate === null
    ? DateTime.now()
    : originalDate instanceof Date
      ? DateTime.fromJSDate(originalDate)
      : originalDate;

  // Apply duration adjustment if provided
  if (duration) {
    const luxonDuration = Duration.fromObject(duration);
    adjustedDateTime = previousDate
      ? adjustedDateTime.minus(luxonDuration)
      : adjustedDateTime.plus(luxonDuration);
  }

  // Set to start of day if requested
  if (startOfDay) {
    adjustedDateTime = adjustedDateTime.startOf('day');
  }

  // Return in the requested format
  switch (returnType) {
    case TimeReturnType.STR_FORMAT:
      try {
        return adjustedDateTime;
      } catch (e: any) {
        throw new Error(`Invalid date format: ${dateFormat}. Error: ${e.message}`);
      }
    case TimeReturnType.DATETIME:
      return adjustedDateTime.toFormat(dateFormat);
    case TimeReturnType.DATE:
      return adjustedDateTime.toJSDate();
    case TimeReturnType.MS:
      return adjustedDateTime.toMillis();
    default:
      throw new Error(`Invalid return type: ${returnType}`);
  }
}

// Re-export enums for use elsewhere
export { TimeDeltaType, TimeReturnType };
