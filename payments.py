"""토스페이먼츠 연동 준비용 골격. 지금은 데모 주문만 사용합니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PaymentResult:
    ok: bool
    mode: str
    message: str
    data: dict[str, Any] | None = None


def create_payment(
    *,
    amount: int,
    order_id: str,
    order_name: str,
    customer_name: str,
    client_key: str,
    payment_mode: str = "demo",
) -> PaymentResult:
    """결제 세션 생성. bank/demo면 바로 통과, toss면 키 확인만 합니다."""
    if payment_mode == "bank":
        return PaymentResult(
            ok=True,
            mode="bank",
            message="주문이 접수되었습니다. 안내에 따라 계좌로 입금해 주세요.",
            data={
                "amount": amount,
                "order_id": order_id,
                "order_name": order_name,
                "customer_name": customer_name,
            },
        )

    if payment_mode != "toss":
        return PaymentResult(
            ok=True,
            mode="demo",
            message="연습 주문으로 처리됩니다. 실제 카드 결제는 되지 않습니다.",
            data={
                "amount": amount,
                "order_id": order_id,
                "order_name": order_name,
                "customer_name": customer_name,
            },
        )

    if not client_key:
        return PaymentResult(
            ok=False,
            mode="toss",
            message="TOSS_CLIENT_KEY가 없습니다. config 또는 환경변수를 설정하세요.",
        )

    # 실연동 시: 토스 결제위젯/결제창 SDK에 orderId·amount·customerName 전달
    return PaymentResult(
        ok=True,
        mode="toss",
        message="토스페이먼츠 키가 설정되어 있습니다. 프론트 SDK 연결이 필요합니다.",
        data={
            "client_key": client_key,
            "amount": amount,
            "order_id": order_id,
            "order_name": order_name,
            "customer_name": customer_name,
        },
    )


def confirm_payment(
    *,
    payment_key: str,
    order_id: str,
    amount: int,
    secret_key: str,
    payment_mode: str = "demo",
) -> PaymentResult:
    """결제 승인. demo면 키 없이 성공 처리."""
    if payment_mode != "toss":
        return PaymentResult(
            ok=True,
            mode="demo",
            message="데모 결제가 승인된 것으로 처리했습니다.",
            data={"order_id": order_id, "amount": amount},
        )

    if not secret_key or not payment_key:
        return PaymentResult(
            ok=False,
            mode="toss",
            message="TOSS_SECRET_KEY 또는 paymentKey가 없습니다.",
        )

    # 실연동 시: POST https://api.tosspayments.com/v1/payments/confirm
    return PaymentResult(
        ok=False,
        mode="toss",
        message="토스 승인 API는 사업자·계약 후 연결하세요. 지금은 호출하지 않습니다.",
        data={
            "payment_key": payment_key,
            "order_id": order_id,
            "amount": amount,
        },
    )
