import nextra from 'nextra'
import remarkEmail from './remark/email.mjs'
import remarkFigures from './remark/figures.mjs'

const withNextra = nextra({
  search: { codeblocks: false },
  mdxOptions: { remarkPlugins: [remarkEmail, remarkFigures] }
})

export default withNextra({
  output: 'export',
  // Keeps pages at en/user-guide.html, the addresses the site has always had.
  trailingSlash: false,
  images: { unoptimized: true },
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? '',
  reactStrictMode: true,
  i18n: { locales: ['en', 'de'], defaultLocale: 'en' }
})
