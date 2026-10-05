// Chinese review layout based on the repository's IEEE A4 conference template.
// This is not an IEEE-certified submission template or PDF eXpress validation.
#set page(paper: "a4", margin: (top: 19mm, bottom: 24mm, left: 15.7mm, right: 15.7mm),
  numbering: "1", number-align: center)
#set text(font: ("Nimbus Roman", "Droid Sans Fallback"), size: 10pt, lang: "zh")
#set par(justify: true, leading: 0.45em, first-line-indent: 1em)
#set heading(numbering: none)
#set block(spacing: 0.65em)
#set image(width: 100%)
#set figure(numbering: none, gap: 4pt)
#set table(stroke: 0.35pt, inset: 3pt)
#show table: set text(size: 8pt)
#show figure.caption: set text(size: 8pt)
#show heading.where(level: 2): it => block(above: 11pt, below: 6pt)[
  #align(center, text(size: 10pt, weight: "bold", it.body))
]
#show heading.where(level: 3): it => block(above: 8pt, below: 4pt)[
  #text(size: 9pt, weight: "bold", it.body)
]
#show heading.where(level: 4): it => block(above: 6pt, below: 3pt)[
  #text(size: 9pt, weight: "bold", it.body)
]
#let paper-equation(body, number) = block(above: 6pt, below: 6pt)[
  #set par(first-line-indent: 0pt)
  #set text(size: 9pt)
  #layout(size => {
    let eq = math.equation(body, block: true, numbering: none)
    let natural = measure(eq)
    let available = size.width - 22pt
    let ratio = calc.min(1, available / natural.width)
    grid(columns: (1fr, 21pt), gutter: 1pt, align: (center + horizon, right + horizon),
      scale(x: ratio * 100%, y: ratio * 100%, reflow: true, eq),
      text(size: 8pt, [(#number)]))
  })
]
#let blank-figure(caption) = block(breakable: false, above: 5pt, below: 7pt)[
  #rect(width: 100%, height: 29mm, stroke: 0.35pt + luma(180))
  #v(3pt)
  #set par(first-line-indent: 0pt)
  #text(size: 8pt, caption)
]
