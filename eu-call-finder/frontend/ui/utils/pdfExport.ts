import jsPDF from 'jspdf';
import { FundingCard } from '../types';

export const exportProjectToPDF = (card: FundingCard, companyName: string = 'Your Company') => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;
  const margin = 20;
  const contentWidth = pageWidth - (margin * 2);
  
  let yPos = 20;
  
  // Helper function to add section header
  const addSectionHeader = (title: string) => {
    yPos += 8;
    doc.setFillColor(139, 184, 232); // Primary blue
    doc.rect(margin, yPos - 5, contentWidth, 8, 'F');
    doc.setFontSize(12);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(title, margin + 3, yPos);
    yPos += 10;
  };
  
  // Typography constants for a more "real PDF" look (consistent leading, margins)
  const BASE_FONT = 10;
  const BASE_LEADING = 1.35; // line-height multiplier

  // Helper: ensure there's enough vertical space, otherwise start a new page.
  const ensureSpace = (neededHeight: number, bottomMargin: number = 20) => {
    const pageHeight = doc.internal.pageSize.height;
    if (yPos + neededHeight > pageHeight - bottomMargin) {
      doc.addPage();
      yPos = 20;
    }
  };

  // Helper function to add wrapped text with consistent leading and optional justification.
  // NOTE: jsPDF justification is approximate; we use it only for body paragraphs.
  const addWrappedText = (
    text: string,
    x: number,
    maxWidth: number,
    fontSize: number = BASE_FONT,
    options?: { align?: 'left' | 'justify'; leading?: number }
  ) => {
    const align = options?.align ?? 'left';
    const leading = options?.leading ?? BASE_LEADING;

    doc.setFontSize(fontSize);

    // Normalize whitespace but keep paragraphs separated.
    const paragraphs = (text ?? '')
      .replace(/\r\n/g, '\n')
      .split('\n')
      .map(p => p.replace(/\s+/g, ' ').trim())
      .filter(Boolean);

    const lineHeight = fontSize * 0.3528 * leading; // pt -> mm (approx) * leading

    let renderedLines = 0;

    for (let pIdx = 0; pIdx < paragraphs.length; pIdx++) {
      const p = paragraphs[pIdx];
      const lines = doc.splitTextToSize(p, maxWidth);
      ensureSpace(lines.length * lineHeight + 2);

      if (align === 'justify' && lines.length > 1) {
        // Justify all lines except last line of the paragraph.
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i] as string;
          if (i === lines.length - 1) {
            doc.text(line, x, yPos, { maxWidth, align: 'left' });
          } else {
            doc.text(line, x, yPos, { maxWidth, align: 'justify' });
          }
          yPos += lineHeight;
          renderedLines += 1;
        }
      } else {
        doc.text(lines, x, yPos, { maxWidth, align: 'left' });
        yPos += lines.length * lineHeight;
        renderedLines += lines.length;
      }

      // Paragraph spacing
      if (pIdx < paragraphs.length - 1) yPos += lineHeight * 0.35;
    }

    return renderedLines;
  };
  
  // Header with logo-like styling
  doc.setFillColor(139, 184, 232);
  doc.roundedRect(margin, 10, contentWidth, 25, 3, 3, 'F');
  doc.setFontSize(18);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text('EuroFund Finder', margin + 5, 22);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('EU Funding Opportunity Report', margin + 5, 30);
  
  yPos = 42;
  
  // Project Title
  doc.setFontSize(16);
  doc.setTextColor(107, 158, 212);
  doc.setFont('helvetica', 'bold');
  const titleLines = addWrappedText(card.title, margin, contentWidth, 16);
  yPos += 5;
  
  // Programme
  if (card.programme) {
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.setFont('helvetica', 'italic');
    doc.text(`Programme: ${card.programme}`, margin, yPos);
    yPos += 8;
  }
  
  // Key Metrics Box
  doc.setDrawColor(139, 184, 232);
  doc.setLineWidth(0.5);
  doc.roundedRect(margin, yPos, contentWidth, 35, 3, 3, 'S');
  
  // Match Score
  doc.setFillColor(card.match_percentage >= 80 ? 34 : card.match_percentage >= 70 ? 59 : 234, 
                   card.match_percentage >= 80 ? 197 : card.match_percentage >= 70 ? 130 : 179, 
                   card.match_percentage >= 80 ? 94 : card.match_percentage >= 70 ? 246 : 8);
  doc.roundedRect(margin + 5, yPos + 5, 50, 12, 2, 2, 'F');
  doc.setFontSize(11);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text(`${card.match_percentage}% Match`, margin + 8, yPos + 13);
  
  // Eligibility Badge
  if (card.eligibility_passed) {
    doc.setFillColor(34, 197, 94);
    doc.roundedRect(margin + 60, yPos + 5, 40, 12, 2, 2, 'F');
    doc.text('ELIGIBLE', margin + 65, yPos + 13);
  }
  
  // Budget & Deadline row
  doc.setFontSize(9);
  doc.setTextColor(50, 50, 50);
  doc.setFont('helvetica', 'bold');
  doc.text('Budget:', margin + 5, yPos + 26);
  doc.setFont('helvetica', 'normal');
  doc.text(card.budget, margin + 25, yPos + 26);
  
  if (card.contribution && card.contribution !== 'N/A') {
    doc.setFont('helvetica', 'bold');
    doc.text('EU Contribution:', margin + 80, yPos + 26);
    doc.setFont('helvetica', 'normal');
    doc.text(card.contribution, margin + 120, yPos + 26);
  }
  
  // Deadline
  doc.setFont('helvetica', 'bold');
  doc.text('Deadline:', margin + 5, yPos + 32);
  doc.setTextColor(220, 38, 38);
  doc.setFont('helvetica', 'normal');
  doc.text(card.deadline, margin + 28, yPos + 32);
  
  yPos += 42;
  
  // Description Section
  addSectionHeader('Description');
  doc.setTextColor(50, 50, 50);
  doc.setFont('helvetica', 'normal');
  const description = card.description || card.short_summary || card.why_recommended || 'No description available';
  addWrappedText(description, margin, contentWidth, 10, { align: 'justify' });
  yPos += 5;
  
  // Why Recommended
  if (card.why_recommended && card.why_recommended !== description) {
    doc.setFontSize(11);
    doc.setTextColor(139, 184, 232);
    doc.setFont('helvetica', 'bold');
    doc.text('Why This Project is Recommended:', margin, yPos, { maxWidth: contentWidth });
    yPos += 6;
    doc.setTextColor(50, 50, 50);
    doc.setFont('helvetica', 'normal');
    addWrappedText(card.why_recommended, margin, contentWidth, 10, { align: 'justify' });
    yPos += 3;
  }
  
  // Tags
  if (card.tags && card.tags.length > 0) {
    yPos += 3;
    doc.setFontSize(9);
    doc.setTextColor(139, 184, 232);
    doc.setFont('helvetica', 'bold');
    doc.text('Tags: ', margin, yPos);
    doc.setTextColor(100, 100, 100);
    doc.setFont('helvetica', 'normal');
    const tagsText = card.tags.slice(0, 10).join(' • ');
    const tagLines = doc.splitTextToSize(tagsText, contentWidth - 15);
    doc.text(tagLines, margin + 12, yPos);
    yPos += (tagLines.length * 4);
  }
  
  // Check for new page
  ensureSpace(40);
  
  // Project Summary (if available)
  if (card.project_summary) {
    addSectionHeader('Project Analysis');
    
    if (card.project_summary.overview) {
      doc.setFontSize(10);
      doc.setTextColor(139, 184, 232);
      doc.setFont('helvetica', 'bold');
      doc.text('Overview:', margin, yPos, { maxWidth: contentWidth });
      yPos += 5;
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');
      addWrappedText(card.project_summary.overview, margin, contentWidth, 10, { align: 'justify' });
      yPos += 3;
    }
    
    if (card.project_summary.company_fit_assessment) {
      yPos += 3;
      doc.setFontSize(10);
      doc.setTextColor(139, 184, 232);
      doc.setFont('helvetica', 'bold');
      doc.text('Company Fit Assessment:', margin, yPos, { maxWidth: contentWidth });
      yPos += 5;
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');
      addWrappedText(card.project_summary.company_fit_assessment, margin, contentWidth, 10, { align: 'justify' });
      yPos += 3;
    }
    
    if (card.project_summary.key_alignment_points && card.project_summary.key_alignment_points.length > 0) {
      yPos += 5;
      ensureSpace(18);
      doc.setFontSize(10);
      doc.setTextColor(34, 197, 94);
      doc.setFont('helvetica', 'bold');
      doc.text('✓ Key Alignment Points:', margin, yPos, { maxWidth: contentWidth });
      yPos += 5;
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');

      const bulletIndent = 7;
      const bulletGap = 3;
      const bulletMaxWidth = contentWidth - bulletIndent;
      const bulletLineHeight = 10 * 0.3528 * BASE_LEADING;

      card.project_summary.key_alignment_points.forEach((point) => {
        const p = (point ?? '').toString().trim();
        if (!p) return;
        const lines = doc.splitTextToSize(p, bulletMaxWidth - bulletGap);
        ensureSpace(lines.length * bulletLineHeight + 2);

        // bullet
        doc.text('•', margin + 5, yPos);
        // wrapped text
        doc.text(lines, margin + 5 + bulletIndent, yPos, { maxWidth: bulletMaxWidth - bulletGap });
        yPos += lines.length * bulletLineHeight + 1;
      });
    }
    
    if (card.project_summary.potential_challenges && card.project_summary.potential_challenges.length > 0) {
      yPos += 3;
      ensureSpace(18);
      doc.setFontSize(10);
      doc.setTextColor(234, 179, 8);
      doc.setFont('helvetica', 'bold');
      doc.text('⚠ Potential Challenges:', margin, yPos, { maxWidth: contentWidth });
      yPos += 5;
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');

      const bulletIndent = 7;
      const bulletGap = 3;
      const bulletMaxWidth = contentWidth - bulletIndent;
      const bulletLineHeight = 10 * 0.3528 * BASE_LEADING;

      card.project_summary.potential_challenges.forEach((challenge) => {
        const c = (challenge ?? '').toString().trim();
        if (!c) return;
        const lines = doc.splitTextToSize(c, bulletMaxWidth - bulletGap);
        ensureSpace(lines.length * bulletLineHeight + 2);

        doc.text('•', margin + 5, yPos);
        doc.text(lines, margin + 5 + bulletIndent, yPos, { maxWidth: bulletMaxWidth - bulletGap });
        yPos += lines.length * bulletLineHeight + 1;
      });
    }
    
    if (card.project_summary.recommendation) {
      yPos += 3;
      doc.setFontSize(10);
      doc.setTextColor(139, 184, 232);
      doc.setFont('helvetica', 'bold');
      doc.text('Recommendation:', margin, yPos, { maxWidth: contentWidth });
      yPos += 5;
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');
      addWrappedText(card.project_summary.recommendation, margin, contentWidth, 10, { align: 'justify' });
      yPos += 3;
    }
  }
  
  // Check for new page
  ensureSpace(40);
  
  // Key Benefits
  if (card.key_benefits && card.key_benefits.length > 0) {
    addSectionHeader('Key Benefits');
    doc.setFontSize(10);
    doc.setTextColor(50, 50, 50);
    doc.setFont('helvetica', 'normal');
    card.key_benefits.forEach((benefit) => {
      doc.setTextColor(34, 197, 94);
      doc.text('★', margin + 3, yPos);
      doc.setTextColor(50, 50, 50);
      const lines = addWrappedText(benefit, margin + 10, contentWidth - 10);
      yPos += 3;
    });
  }
  
  // Check for new page
  ensureSpace(40);
  
  // Action Items
  if (card.action_items && card.action_items.length > 0) {
    addSectionHeader('Action Items');
    doc.setFontSize(10);
    doc.setTextColor(50, 50, 50);
    doc.setFont('helvetica', 'normal');
    card.action_items.forEach((item, index) => {
      doc.setTextColor(139, 184, 232);
      doc.setFont('helvetica', 'bold');
      doc.text(`${index + 1}.`, margin + 3, yPos);
      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'normal');
      const lines = addWrappedText(item, margin + 12, contentWidth - 12);
      yPos += 3;
    });
  }
  
  // Check for new page
  ensureSpace(40);
  
  // Domain Matches
  // UX: Remove "undefined" / empty items and avoid rendering this whole section when useless.
  const cleanedDomainMatches = (card.domain_matches || [])
    .filter((m) => {
      const domain = (m?.domain ?? '').toString().trim();
      const relevance = (m?.relevance ?? '').toString().trim();
      if (!domain) return false;
      if (domain.toLowerCase() === 'undefined') return false;
      // If both are "undefined"-ish, drop.
      if (relevance && relevance.toLowerCase() === 'undefined') return false;
      return true;
    })
    // De-duplicate by domain label
    .filter((m, idx, arr) => {
      const d = (m.domain ?? '').toString().trim().toLowerCase();
      return arr.findIndex(x => (x.domain ?? '').toString().trim().toLowerCase() === d) === idx;
    });

  if (cleanedDomainMatches.length > 0) {
    addSectionHeader('Domain Matches');
    doc.setFontSize(10);
    cleanedDomainMatches.forEach((match) => {
      // Ensure we don't draw beyond the page bottom
      ensureSpace(14);

      doc.setTextColor(50, 50, 50);
      doc.setFont('helvetica', 'bold');
      doc.text(`• ${match.domain}`, margin + 3, yPos, { maxWidth: contentWidth - 6 });
      yPos += 5;
      if (match.relevance) {
        doc.setTextColor(100, 100, 100);
        doc.setFont('helvetica', 'italic');
        const relText = `  ${match.relevance}`;
        const relLines = doc.splitTextToSize(relText, contentWidth - 15);
        ensureSpace(relLines.length * 5 + 2);
        doc.text(relLines, margin, yPos, { maxWidth: contentWidth });
        yPos += (relLines.length * 5) + 2;
      }
    });
  }
  
  // Suggested Partners
  if (card.suggested_partners && card.suggested_partners.length > 0) {
    yPos += 5;
    addSectionHeader('Suggested Partners');
    doc.setFontSize(10);
    doc.setTextColor(50, 50, 50);
    doc.setFont('helvetica', 'normal');

    const itemLineHeight = 10 * 0.3528 * BASE_LEADING;
    const numIndent = 8;

    card.suggested_partners.forEach((partner, index) => {
      const p = (partner ?? '').toString().trim();
      if (!p) return;

      const prefix = `${index + 1}.`;
      const lines = doc.splitTextToSize(p, contentWidth - 5 - numIndent);
      ensureSpace(lines.length * itemLineHeight + 2);

      doc.setFont('helvetica', 'bold');
      doc.text(prefix, margin + 5, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(lines, margin + 5 + numIndent, yPos, { maxWidth: contentWidth - 5 - numIndent });
      yPos += lines.length * itemLineHeight + 1;
    });
  }
  
  // Success Probability
  if (card.success_probability) {
    yPos += 5;
    const probColor = card.success_probability === 'high' ? [34, 197, 94] : 
                     card.success_probability === 'medium' ? [59, 130, 246] : [234, 179, 8];
    doc.setFillColor(probColor[0], probColor[1], probColor[2]);
    doc.roundedRect(margin, yPos, 80, 20, 3, 3, 'F');
    doc.setFontSize(11);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(`Success Probability: ${card.success_probability.toUpperCase()}`, margin + 5, yPos + 13);
    yPos += 28;
  }
  
  // Check for new page before URL
  ensureSpace(60);
  
  // Project Link Section
  const linkBoxHeight = 40;
  doc.setDrawColor(139, 184, 232);
  doc.setLineWidth(1);
  doc.roundedRect(margin, yPos, contentWidth, linkBoxHeight, 5, 5, 'S');
  doc.setFillColor(240, 248, 255);
  doc.roundedRect(margin, yPos, contentWidth, linkBoxHeight, 5, 5, 'F');
  
  yPos += 8;
  doc.setFontSize(11);
  doc.setTextColor(139, 184, 232);
  doc.setFont('helvetica', 'bold');
  doc.text('Apply for this Funding Opportunity', margin + 10, yPos);
  yPos += 8;
  doc.setFontSize(9);
  doc.setTextColor(0, 100, 200);
  doc.setFont('helvetica', 'normal');
  
  // Truncate URL if too long
  const maxUrlWidth = contentWidth - 20;
  let displayUrl = card.url;
  const urlWidth = doc.getTextWidth(card.url);
  if (urlWidth > maxUrlWidth) {
    // Calculate how many characters fit
    const avgCharWidth = urlWidth / card.url.length;
    const maxChars = Math.floor(maxUrlWidth / avgCharWidth) - 3;
    displayUrl = card.url.substring(0, maxChars) + '...';
  }
  doc.textWithLink(displayUrl, margin + 10, yPos, { url: card.url });
  yPos += 8;
  doc.setFontSize(8);
  doc.setTextColor(100, 100, 100);
  doc.text('Click the link above to visit the official funding portal', margin + 10, yPos);
  
  yPos += 25;
  
  // Footer
  doc.setDrawColor(200, 200, 200);
  doc.line(margin, 280, pageWidth - margin, 280);
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  doc.setFont('helvetica', 'italic');
  doc.text(`Generated by EuroFund Finder for ${companyName} on ${new Date().toLocaleDateString()}`, margin, 288);
  doc.text(`Project ID: ${card.id}`, pageWidth - margin - 50, 288);
  
  // Save PDF
  const filename = `${card.title.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50)}_funding_project.pdf`;
  doc.save(filename);
};
