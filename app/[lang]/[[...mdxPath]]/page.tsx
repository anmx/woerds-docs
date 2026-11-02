import { generateStaticParamsFor, importPage } from 'nextra/pages'
import { useMDXComponents } from '../../../mdx-components'

type Props = { params: Promise<{ lang: string; mdxPath?: string[] }> }

export const generateStaticParams = generateStaticParamsFor('mdxPath', 'lang')

export async function generateMetadata({ params }: Props) {
  const { lang, mdxPath } = await params
  const { metadata } = await importPage(mdxPath, lang)
  return metadata
}

export default async function Page({ params }: Props) {
  const { lang, mdxPath } = await params
  const { default: MDXContent, toc, metadata, sourceCode } = await importPage(mdxPath, lang)
  const Wrapper = useMDXComponents().wrapper as React.ComponentType<Record<string, unknown>>
  return (
    <Wrapper toc={toc} metadata={metadata} sourceCode={sourceCode}>
      <MDXContent params={await params} />
    </Wrapper>
  )
}
