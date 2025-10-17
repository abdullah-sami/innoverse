 const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (currentStep === 3) {
      setStep3Error("");

      if (!paymentPhone.trim() || !transactionId.trim()) {
        setStep3Error(
          "Please enter your payment phone number and transaction ID."
        );
        return;
      }

      const competitionCodeMap: { [key: string]: string } = {
        "Science Olympiad": "sc_olym",
        "Competitive Programming": "programming",
        "Math Maestros": "m_maestros",
        "Research Article": "r_article",
        "3-Minute Research": "3m-res",
      };

      const teamCompetitionCodeMap: { [key: string]: string } = {
        "Robo Soccer": "robo_soccer",
        "Line Forwarding Robot": "lfr",
        "Qwizard Mania": "q_mania",
        "Project Showcasing": "pr_show",
      };

      const registrationData: RegistrationData = {
        participant: {
          full_name: formData.fullName,
          gender: formData.gender === "male" ? "M" : "F",
          email: formData.email,
          grade: formData.grade,
          phone: formData.contactNumber,
          institution: formData.instituteName,
          address: formData.address,
          t_shirt_size: formData.tshirtSize.toUpperCase(),
        },
        payment: {
          amount: totalAmount.toFixed(2),
          method: paymentMethod,
          phone: paymentPhone,
          trx_id: transactionId,
        },
      };

      if (formData.guardianContact.trim()) {
        registrationData.participant.guardian_contact =
          formData.guardianContact;
      }

      const selectedSoloCompetitions = soloCompetitions
        .filter((c) => c.selected)
        .map((c) => competitionCodeMap[c.name]);

      registrationData.competition = [...(selectedSoloCompetitions || [])];

      const selectedTeamCompetitions = teamCompetitions.filter(
        (c) => c.selected
      );
      if (selectedTeamCompetitions.length > 0) {
        registrationData.team_competition = {
          team: {
            team_name: teamName,
            participant: teamMembers
              .filter(
                (member) =>
                  member.fullName.trim() &&
                  member.grade.trim() &&
                  member.tshirtSize.trim() &&
                  member.phoneNumber.trim() &&
                  member.instituteName.trim() &&
                  member.email.trim()
              )
              .map((member) => ({
                full_name: member.fullName,
                gender: member.gender === "male" ? "M" : "F",
                phone: member.phoneNumber,
                grade: member.grade,
                institution: member.instituteName,
                email: member.email,
                t_shirt_size: member.tshirtSize.toUpperCase(),
              })),
          },
          competition: selectedTeamCompetitions.map(
            (c) => teamCompetitionCodeMap[c.name]
          ),
        };
      }

      console.log(
        "Registration Data:",
        JSON.stringify(registrationData, null, 2)
      );

      // ✅ Send to backend
      try {
        const response = await fetch(
          "http://innoversebd.bdix.cloud/api/register/",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(registrationData),
          }
        );

        if (!response.ok) {
          throw new Error(Server error: ${response.status});
        }

        const result = await response.json();
        console.log("✅ Registration Successful:", result);

        alert("Registration successful!");
        // You can reset your form or redirect here
      } catch (error) {
        console.error("❌ Registration Failed:", error);
        alert("Registration failed. Please try again.");
      }
    }
  };
innoversebd.bdix.cloud