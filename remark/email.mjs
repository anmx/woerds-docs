const EMAIL = /([\w.+-]+) _at_ ([\w-]+) _dot_ ([\w.-]+)/g

const span = (className, children) => ({
  type: 'emphasis',
  data: { hName: 'span', hProperties: { className } },
  children
})

// Addresses written as "name _at_ host _dot_ tld" get a hidden decoy part, so that harvesters copying the text get a
// wrong address.
function split(value) {
  const nodes = []
  let last = 0
  for (const match of value.matchAll(EMAIL)) {
    const [whole, name, host, tld] = match
    if (match.index > last) nodes.push({ type: 'text', value: value.slice(last, match.index) })
    nodes.push(
      span('email', [
        { type: 'text', value: `${name}@` },
        span('decoy', [{ type: 'text', value: 'no.spam.' }]),
        { type: 'text', value: `${host}.${tld}` }
      ])
    )
    last = match.index + whole.length
  }
  if (last === 0) return null
  if (last < value.length) nodes.push({ type: 'text', value: value.slice(last) })
  return nodes
}

// Markdown reads _at_ and _dot_ as emphasis, so they first have to become text again.
function restoreMarkers(children) {
  const restored = []
  for (const child of children) {
    const marker = child.type === 'emphasis' && child.children.length === 1 && child.children[0].value
    const node = marker === 'at' || marker === 'dot' ? { type: 'text', value: `_${marker}_` } : child
    const previous = restored.at(-1)
    if (node.type === 'text' && previous?.type === 'text') previous.value += node.value
    else restored.push(node.type === 'text' ? { ...node } : node)
  }
  return restored
}

function walk(node) {
  if (!node.children) return
  node.children = restoreMarkers(node.children).flatMap(child => {
    if (child.type === 'text') return split(child.value) ?? [child]
    walk(child)
    return [child]
  })
}

export default function remarkEmail() {
  return walk
}
