import type { ComponentPropsWithoutRef } from 'react'

/** Agrupa ações com o espaçamento padrão, preservando os atributos do contêiner. */
export default function Actions({ className, ...props }: ComponentPropsWithoutRef<'div'>) {
  const containerClassName = ['actions', className].filter(Boolean).join(' ')

  return <div {...props} className={containerClassName} />
}
