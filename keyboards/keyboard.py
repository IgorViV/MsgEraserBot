from telethon import Button
from lexicon.lexicon import LEXICON_RU
from telethon.tl.types import (
    InputKeyboardButtonRequestPeer,
    RequestPeerTypeBroadcast,
    RequestPeerTypeChat,
    RequestPeerTypeUser
)

selection_button_list = [
        [
            InputKeyboardButtonRequestPeer(
                text=LEXICON_RU['button_select_channel'],
                button_id=1,
                max_quantity=1,
                peer_type=RequestPeerTypeBroadcast(),
                username_requested=True
            ),
            InputKeyboardButtonRequestPeer(
                text=LEXICON_RU['button_select_chat'],
                button_id=2,
                max_quantity=1,
                peer_type=RequestPeerTypeChat(),
                username_requested=True
            )
        ],
        [
            InputKeyboardButtonRequestPeer(
                text=LEXICON_RU['button_select_user'],
                button_id=3,
                max_quantity=1,
                peer_type=RequestPeerTypeUser(bot=False),
                username_requested=True
            ),
        ]
    ]

period_buttons = [
        [
            Button.inline("🗑️ Старше 7 дней", b'7_days'),
            Button.inline("🗑️ Старше 30 дней", b'30_days')
        ],
        [
            Button.inline("🗑️ Старше 60 дней", b'60_days'),
            Button.inline("🗑️ Старше 90 дней", b'90_days')
        ],
        [
            Button.inline("❌ Отмена", b'cancel')
        ]
    ]