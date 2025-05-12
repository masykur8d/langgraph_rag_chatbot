message_hover_animation = 'transition delay-150 duration-300 ease-in-out hover:-translate-y-1 hover:scale-105'

slide_up_bounce = r"""
    <style>
    @keyframes slideUpBounce {
    0% {
        transform: translateY(100%); /* Start fully hidden */
    }
    70% {
        transform: translateY(-10px); /* Overshoot */
    }
    90% {
        transform: translateY(5px); /* Slight rebound */
    }
    100% {
        transform: translateY(0); /* Settle in final position */
    }
    }
    </style>
"""

pulse_custom = r'''
<style>
@keyframes pulseCustom {
    0%, 100% {
        transform: scale(1);
        opacity: 1; /* Ensure opacity doesn't change */
    }
    50% {
        transform: scale(1.4);
        opacity: 1; /* Keep it visible during the animation */
    }
}
.pulse-custom {
    animation: pulseCustom 1s infinite;
}
</style>
'''