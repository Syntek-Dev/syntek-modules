/**
 * Form state type definitions
 *
 * Types for form validation, errors, and submission states.
 */

export interface FormErrors<T = Record<string, string>> {
  [key: string]: string | undefined;
}

export type ValidationState = 'idle' | 'validating' | 'valid' | 'invalid';

export type SubmitState = 'idle' | 'submitting' | 'success' | 'error';

export interface FormState<T> {
  values: T;
  errors: FormErrors<T>;
  touched: Record<keyof T, boolean>;
  validationState: ValidationState;
  submitState: SubmitState;
  submitError?: string;
}

export interface FieldValidation {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | undefined;
}

export interface FormValidation<T> {
  [K in keyof T]?: FieldValidation;
}
