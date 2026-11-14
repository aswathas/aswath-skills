---
name: aswath-delivery
description: "Use when finished work goes back to a person on a chat channel — WhatsApp above all — and the chat must hold only the final version. Purges the superseded messages and files, sends the current build once, and leaves one clean final state. Triggers: \"send him the final files\", \"delete the old messages\", \"clean up the chat\", \"only the final version\", \"deliver the report\", \"remove the unwanted messages from whatsapp\", \"delivery\"."
---

# aswath-delivery

The other end of `aswath-thevai`. That skill collects the brief; this one hands back the work.

The failure mode this exists to prevent: a chat that has accumulated four copies of the report, two dead links and a paragraph of "sent, sorry, here it is again" — where the person cannot tell which file is the real one, and the stale one is what they open for their viva.

A chat is a shelf, not a ledger. What matters is not what was sent; it is what is there when the person looks.

## The order

Delete first, then send. Sending first leaves a window where both the old and the new file exist, and the person may already have opened the old one.

1. **Read the chat.** List the messages, yours and theirs, with the ids. Know what is actually there before you remove anything.
2. **Mark what is superseded.** Your old files. Your old status messages that describe a state that no longer exists. Your old links if the address changed. A file you sent twice.
3. **Delete those, and only those.** Then send the current build.
4. **Delete the staging copies.** The files you put in the channel's media folder to make them sendable go away afterwards.
5. **Say what you did.** One line to the owner of the work: what was removed, what was sent.

## What stays

- **Their messages.** Always. They are the record of what was asked for, and they are not yours to remove.
- **The requirement conversation.** Your answers to their questions stay. They are the evidence that the work was built to a brief.
- **The final files.** The current build, sent once.
- **The live link and the access code.** If there is one, it stays and it stays correct.

## What goes

- **Every earlier copy of a file you are about to replace.** Including duplicates you sent by accident. Two identical PDFs in a chat is a defect, not a redundancy.
- **Status messages that are now false.** "The old link died, here is the new one" is wrong the moment there is a newer link. "Built and ready, tell me what to change" is wrong the moment it has been changed.
- **Any note that the final note replaces.**

## The final message

One message. It carries:

- the thing itself (the file, or the link, with the access code);
- what changed since they last heard from you, in one line;
- nothing else. No "sent!", no "done", no second copy.

Warm, brief, in their language. The chat-native rules in `aswath-thevai` apply to the last message too: no markdown headings, no tables, no code fences.

## Rules

**Never send a file you have not verified.** Open it, or check the build output that produced it. A link that is dead by the time the message lands is worse than no link: check the health path before sending, not after.

**Never send a file the code does not back.** If the build changed, the report and the deck changed with it. Deliver the rebuilt files, never the ones on disk from before the last change.

**One build, one send.** If two tools produce the same deliverable, pick one and send that. If a deliverable is a document and a deck, they are two files and both may be needed — but each is sent once.

**Deleting is not cancelling.** A deleted file is gone from their chat. Delete only what you are replacing, and only after you know the replacement exists.

**The tool's report is the evidence.** A delete that returns a success is done; a send that returns a success is sent. Verify after, not by assuming — read the chat back and check the file is there exactly once.

**Report the clean-up to the owner, not to the person.** The person gets the work; the owner gets one line saying the chat was cleaned and what was removed.

## What this is not

- Not a place to negotiate. The brief was approved in `aswath-thevai`; a delivery that reopens the requirements has failed at the last step.
- Not a place for the build story. The report and the deck carry that. The chat message carries the file and one line of change.
- Not a licence to delete their material — their reference documents, their questions, their files stay untouched.

## With the harness

The channel is the WhatsApp MCP (`mcp__whatsapp__wa_code`): `wa.getMessages`, `wa.deleteMessage` with `confirm: true`, `wa.send` / `wa.sendMessage` with a media path, and `wa.files` for the staging folder.

Copy each deliverable into the channel's media root, send it from there, and remove the copy afterwards. The media root is the only place the channel can read from.
