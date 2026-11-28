import type { ComponentPropsWithRef } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'text'
type ButtonProps = ComponentPropsWithRef<'button'> & {
  variant?: ButtonVariant
}

const variantClassNames: Record<ButtonVariant, string> = {
  primary: '',
  secondary: 'secondary',
  danger: 'danger',
  text: 'textButton',
}

/** Centraliza as variantes visuais e encaminha eventos, atributos e ref ao botão nativo. */
export default function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  const variantClassName = variantClassNames[variant]
  const buttonClassName = variantClassName ? [variantClassName, className].filter(Boolean).join(' ') : className

  return <button {...props} className={buttonClassName} />
}
