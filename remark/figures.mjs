const isBlank = node => node.type === 'text' && node.value.trim() === ''
const text = value => ({ type: 'text', value })
const element = (hName, className, children) => ({
  type: 'figureElement',
  data: { hName, hProperties: className ? { className } : {} },
  children
})

function figure(image) {
  const className = image.url.includes('/tablet/') ? 'wide' : 'shot'
  return element('figure', className, [
    image,
    ...(image.alt ? [element('figcaption', null, [text(image.alt)])] : [])
  ])
}

// A paragraph holding only images is a row of screenshots, each captioned with its alt text.
function walk(node) {
  node.children?.forEach((child, index) => {
    if (child.type !== 'paragraph') return walk(child)
    const content = child.children.filter(c => !isBlank(c))
    if (content.length > 0 && content.every(c => c.type === 'image')) {
      node.children[index] = element('div', 'figures', content.map(figure))
    }
  })
}

export default function remarkFigures() {
  return walk
}
