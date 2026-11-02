import assert from 'node:assert/strict'
import { test } from 'node:test'
import remarkEmail from './email.mjs'
import remarkFigures from './figures.mjs'

const root = (...children) => ({ type: 'root', children })
const paragraph = (...children) => ({ type: 'paragraph', children })
const text = value => ({ type: 'text', value })
const image = (url, alt) => ({ type: 'image', url, alt })

test('an address gets a hidden decoy part', () => {
  const tree = root(paragraph(text('by a _at_ example _dot_ com ("we")')))
  remarkEmail()(tree)
  const [before, email, after] = tree.children[0].children
  assert.equal(before.value, 'by ')
  assert.equal(after.value, ' ("we")')
  assert.equal(email.data.hName, 'span')
  assert.equal(email.data.hProperties.className, 'email')
  assert.deepEqual(
    email.children.map(c => c.value ?? c.children[0].value),
    ['a@', 'no.spam.', 'example.com']
  )
})

test('an address parsed with emphasis is recognized', () => {
  const emphasis = value => ({ type: 'emphasis', children: [text(value)] })
  const tree = root(paragraph(text('a '), emphasis('at'), text(' example '), emphasis('dot'), text(' com')))
  remarkEmail()(tree)
  const email = tree.children[0].children[0]
  assert.equal(email.data.hProperties.className, 'email')
  assert.equal(email.children[0].value, 'a@')
})

test('other emphasis stays emphasis', () => {
  const emphasis = { type: 'emphasis', children: [text('word')] }
  const tree = root(paragraph(text('a '), emphasis))
  remarkEmail()(tree)
  assert.equal(tree.children[0].children[1], emphasis)
})

test('text without an address stays as it is', () => {
  const tree = root(paragraph(text('nothing _at_ all')))
  remarkEmail()(tree)
  assert.deepEqual(tree, root(paragraph(text('nothing _at_ all'))))
})

test('a paragraph of images becomes a row of captioned figures', () => {
  const tree = root(paragraph(image('a/en/1.png', 'One'), text(' '), image('a/tablet/2.png', 'Two')))
  remarkFigures()(tree)
  const row = tree.children[0]
  assert.equal(row.data.hProperties.className, 'figures')
  assert.deepEqual(row.children.map(f => f.data.hProperties.className), ['shot', 'wide'])
  assert.equal(row.children[0].children[1].data.hName, 'figcaption')
  assert.equal(row.children[0].children[1].children[0].value, 'One')
})

test('a paragraph mixing text and images stays a paragraph', () => {
  const tree = root(paragraph(text('see '), image('a.png', 'A')))
  remarkFigures()(tree)
  assert.equal(tree.children[0].type, 'paragraph')
})
