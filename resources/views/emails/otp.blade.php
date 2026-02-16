<div style="font-family: sans-serif; background-color: #f4f4f4; padding: 20px;">
    <div
        style="max-width: 500px; margin: auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #ddd;">
        <!-- Header بالألوان بتاعتك (Dark Cyan) -->
        <div style="background-color: #008080; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">Learnova</h1>
        </div>

        <div style="padding: 30px; text-align: center;">
            <h2 style="color: #333;">Verification Code</h2>
            <p style="color: #666;">Use the code below to reset your password. It will expire in 10 minutes.</p>

            <!-- OTP Box بالألوان بتاعتك (Dark Gray/Black) -->
            <div
                style="margin: 30px 0; padding: 20px; background: #1a1a1a; color: #00efd1; font-size: 40px; font-weight: bold; letter-spacing: 10px; border-radius: 8px;">
                {{ $otp }}
            </div>

            <p style="color: #999; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>

        <div style="background: #1a1a1a; padding: 10px; text-align: center; color: white; font-size: 11px;">
            &copy; {{ date('Y') }} Smart AI Library - Learnova
        </div>
    </div>
</div>
