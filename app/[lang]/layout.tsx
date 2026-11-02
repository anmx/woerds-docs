import type { Metadata } from 'next'
import type { PageMapItem } from 'nextra'
import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head, Search } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import type { ReactNode } from 'react'
import 'nextra-theme-docs/style.css'
import '../site.css'

const REPOSITORY = 'https://github.com/anmx/woerds-docs'

const LABELS = {
  en: { search: 'Search', noResults: 'No results', toc: 'On this page', backToTop: 'Back to top', footer: 'Open source under the Apache License 2.0, without warranty.' },
  de: { search: 'Suchen', noResults: 'Keine Treffer', toc: 'Auf dieser Seite', backToTop: 'Nach oben', footer: 'Offener Quellcode unter der Apache-Lizenz 2.0, ohne Gewähr.' }
} as const

type Lang = keyof typeof LABELS

export const metadata: Metadata = {
  title: { default: 'wörds', template: '%s – wörds' },
  description: 'wörds is a flashcard app for learning languages: vocabulary and verb forms, with spaced repetition, offline.'
}

// Nextra's routes leave out the language and rely on its middleware, which a static export does not have.
function withLanguage<T extends PageMapItem>(items: T[], lang: string): T[] {
  return items.map(item => ({
    ...item,
    ...('route' in item && { route: `/${lang}${item.route === '/' ? '' : item.route}` }),
    ...('children' in item && { children: withLanguage(item.children, lang) })
  }))
}

export function generateStaticParams() {
  return Object.keys(LABELS).map(lang => ({ lang }))
}

export default async function RootLayout({
  children,
  params
}: {
  children: ReactNode
  params: Promise<{ lang: string }>
}) {
  const { lang } = await params
  const labels = LABELS[lang as Lang]
  return (
    <html lang={lang} dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={<Navbar logo={<b>wörds</b>} projectLink={REPOSITORY} />}
          footer={<Footer>{labels.footer}</Footer>}
          pageMap={withLanguage(await getPageMap(`/${lang}`), lang)}
          docsRepositoryBase={`${REPOSITORY}/tree/main`}
          editLink={null}
          feedback={{ content: null }}
          copyPageButton={false}
          toc={{ title: labels.toc, backToTop: labels.backToTop }}
          search={<Search placeholder={labels.search} emptyResult={labels.noResults} />}
          i18n={[
            { locale: 'en', name: 'English' },
            { locale: 'de', name: 'Deutsch' }
          ]}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
