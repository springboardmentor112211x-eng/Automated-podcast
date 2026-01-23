from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap
import os
import uuid

def generate_pdf(topics, episode_summary=None):
    """
    Generates a PDF from topics and episode summary
    Returns path to generated PDF
    """

    os.makedirs("media/pdfs", exist_ok=True)
    file_path = f"media/pdfs/podcast_{uuid.uuid4()}.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "PodC – Podcast Summary")
    y -= 40

    # Episode summary
    if episode_summary:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Episode Summary")
        y -= 20

        c.setFont("Helvetica", 11)
        for line in wrap(episode_summary, 90):
            c.drawString(40, y, line)
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 40

        y -= 20

    # Topics
    for idx, topic in enumerate(topics, 1):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Topic {idx}: {topic.get('title', 'Untitled')}")
        y -= 18

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(
            40,
            y,
            f"{topic.get('start', 0)}s → {topic.get('end', 0)}s"
        )
        y -= 16

        c.setFont("Helvetica", 11)
        for line in wrap(topic.get("summary", ""), 90):
            c.drawString(40, y, line)
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 40

        y -= 20

    c.save()
    return file_path
