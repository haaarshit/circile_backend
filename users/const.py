def getTemplate():
    return  f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Verify Your Email</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                background: #ffffff;
                margin: 20px auto;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: #007bff;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 22px;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                padding: 20px;
                font-size: 16px;
                color: #333;
                text-align: center;
            }}
            .verify-btn {{
                display: inline-block;
                background: #28a745;
                color: white;
                text-decoration: none;
                padding: 12px 20px;
                font-size: 18px;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #777;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                Verify Your Email
            </div>
            <div class="content">
                <p>Hello <strong>{self.full_name}</strong>,</p>
                <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
                <a href="{verification_link}" class="verify-btn">Verify Email</a>
                <p>If the button doesn't work, copy and paste the link below into your browser:</p>
                <p>{verification_link}</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                © {timezone.now().year} CIRCILE. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """