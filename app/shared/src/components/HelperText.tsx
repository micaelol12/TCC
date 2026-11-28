import type { ComponentPropsWithoutRef } from 'react'

type HelperTextProps = ComponentPropsWithoutRef<'p'> & {
  error?: boolean
}

/** Exibe texto auxiliar pequeno e discreto, preservando os atributos do parágrafo. */
export default function HelperText({ error = false, className, ...props }: HelperTextProps) {
  const paragraphClassName = [error ? 'error small' : 'muted small', className].filter(Boolean).join(' ')

  return <p {...props} className={paragraphClassName} />
}
