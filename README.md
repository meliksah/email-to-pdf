# Initialize the project with asdf
asdf install

# Install poetry dependencies
poetry install

# Run the application
poetry run python -m email_to_pdf.cli \
    --host imap.yandex.com \
    --port 993 \
    --username example@example.com \
    --password "example" \
    --from-email search-from@mail.com \
    --subject "Search Subject"