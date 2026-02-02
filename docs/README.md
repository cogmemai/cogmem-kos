# cogmem-kos Documentation

This documentation is built with [Mintlify](https://mintlify.com).

## Structure

```
docs/
├── docs.json              # Mintlify configuration
├── introduction.mdx       # Landing page
├── quickstart.mdx         # Getting started guide
├── platform/              # Platform documentation
│   ├── overview.mdx
│   ├── installation.mdx
│   ├── configuration.mdx
│   └── solo-mode.mdx
├── architecture/          # Architecture documentation
│   ├── overview.mdx
│   ├── contracts.mdx
│   ├── providers.mdx
│   ├── agents.mdx
│   └── retrieval-plans.mdx
├── api-reference/         # API documentation
│   ├── overview.mdx
│   ├── search.mdx
│   ├── items.mdx
│   ├── entities.mdx
│   └── health.mdx
└── cookbooks/             # Tutorials
    ├── overview.mdx
    ├── search-first.mdx
    ├── entity-pages.mdx
    └── integrations.mdx
```

## Local Development

### Install Mintlify CLI

```bash
npm i -g mintlify
```

### Preview Locally

Run from the `docs/` directory:

```bash
mintlify dev
```

View at http://localhost:3000

### Troubleshooting

If `mintlify dev` isn't working:

```bash
mintlify install
```

## Deployment

### GitHub Integration

1. Install the [Mintlify GitHub App](https://dashboard.mintlify.com/settings/organization/github-app)
2. Connect your repository
3. Changes pushed to main are auto-deployed

### Manual Deployment

```bash
mintlify deploy
```

## Writing Documentation

### MDX Format

All pages use MDX (Markdown + JSX components):

```mdx
---
title: "Page Title"
description: "Page description for SEO"
icon: "rocket"
---

# Content

<Card title="Feature" icon="sparkles">
  Description
</Card>
```

### Available Components

- `<Card>` - Clickable card with icon
- `<CardGroup>` - Grid of cards
- `<Tabs>` / `<Tab>` - Tabbed content
- `<Accordion>` - Collapsible section
- `<CodeGroup>` - Multiple code blocks
- `<Note>` - Info callout
- `<Warning>` - Warning callout
- `<ParamField>` - API parameter documentation
- `<ResponseField>` - API response documentation

### Icons

Icons use [Lucide](https://lucide.dev/icons) names:

```mdx
<Card title="Search" icon="magnifying-glass">
```

## Configuration

Edit `docs.json` to change:

- Navigation structure
- Colors and branding
- Logo
- Social links

See [Mintlify docs](https://mintlify.com/docs) for full configuration options.

## Adding New Pages

1. Create a new `.mdx` file in the appropriate directory
2. Add frontmatter with title, description, and icon
3. Add the page path to `docs.json` navigation
4. Preview with `mintlify dev`

## Resources

- [Mintlify Documentation](https://mintlify.com/docs)
- [MDX Syntax](https://mdxjs.com/)
- [Lucide Icons](https://lucide.dev/icons)
